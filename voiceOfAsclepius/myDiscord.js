const {Client, Intents, Collection, MessageAttachment} = require('discord.js');
const client = new Client({intents: [Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]});
const {
    joinVoiceChannel,
    createAudioPlayer,
    createAudioResource,
    AudioPlayerStatus,
    VoiceConnectionStatus,
    entersState, EndBehaviorType, getVoiceConnection,
} = require('@discordjs/voice');
const {token} = require("./config.json")
const fs = require("fs");
const ffmpeg = require('ffmpeg');
var XMLHttpRequest = require('xhr2');
const {pipeline} = require('stream');
const prism = require('prism-media');
const sleep = require('util').promisify(setTimeout);

const popularPodcasts = [];
const player = createAudioPlayer();

client.on("ready", async () => {
    console.log(`Logged in as ${client.user.tag}!`);
    await getPopularPodcasts();
})

client.voiceManager = new Collection()

async function podcastFunctions(message) {
    if (message.content === ">podcast") {
        let resource;
        let podcastToBePlayed = randomPodcast();

        const connection = joinVoiceChannel({
            channelId: message.member.voice.channel.id,
            guildId: message.member.voice.channel.guildId,
            adapterCreator: message.member.voice.channel.guild.voiceAdapterCreator,
        });

        console.log(popularPodcasts[podcastToBePlayed]);
        resource = createAudioResource(popularPodcasts[podcastToBePlayed], {inlineVolume: true});
        resource.volume.setVolume(0.5);
        connection.subscribe(player);

        connection.on(VoiceConnectionStatus.Ready, () => {
            player.play(resource);
        })

        connection.on(VoiceConnectionStatus.Disconnected, async (oldState, newState) => {
            try {
                console.log("Disconnected.")
                await Promise.race([
                    entersState(connection, VoiceConnectionStatus.Signalling, 5_000),
                    entersState(connection, VoiceConnectionStatus.Connecting, 5_000),
                ]);
            } catch (error) {
                connection.destroy();
            }
        });

        player.on('error', error => {
            console.error(`Error: ${error.message} with resource ${error.resource.metadata.title}`);
        });

        player.on(AudioPlayerStatus.Playing, () => {
            console.log('The audio player has started playing!');
        });

        player.on('idle', () => {
            connection.destroy();
        })
    }

    if (message.content === ">pausePod") {
        player.pause();
    }

    if (message.content === ">unPausePod") {
        player.unpause();
    }

    if (message.content === ">stopPod") {
        player.stop();
    }
}

client.on("message", async message => {
    const voiceChannel = message.member.voice.channel
    let connection = client.voiceManager.get(message.channel.guild.id)

    if (message.content === ">record") {

        if (message.member.voice.channel == null) {
            message.channel.send("Please join a channel.");
        } else {
            connection = joinVoiceChannel({
                channelId: message.member.voice.channel.id,
                guildId: message.member.voice.channel.guildId,
                adapterCreator: message.member.voice.channel.guild.voiceAdapterCreator,
                selfDeaf: false,
                selfMute: true,
            });

            client.voiceManager.set(message.channel.guild.id, connection);
            await entersState(connection, VoiceConnectionStatus.Ready, 20e3);
            const receiver = connection.receiver;

            receiver.speaking.on('start', (userId) => {
                if (userId !== message.author.id) return;
                /* create live stream to save audio */
                createListeningStream(receiver, userId, client.users.cache.get(userId));
            });
            return message.channel.send(`🎙️ I am now recording ${voiceChannel.name}`);

        }
    }


    if (message.content === ">stopRecord") {
        const msg = await message.channel.send("Please wait while I am preparing your recording...")
        /* wait for 5 seconds */
        await sleep(5000)
        connection.destroy();
        client.voiceManager.delete(message.channel.guild.id)
        const filename = "./records/audio";

        /* Create ffmpeg command to convert pcm to mp3 */
        const process = new ffmpeg(`${filename}.pcm`)
        console.log(process.toString());
        process.then(function (audio) {
            audio.fnExtractSoundToMP3(`${filename}.mp3`, async function (error, file) {
                //edit message with recording as attachment
               /* await msg.edit({
                    content: `🔉 Here is your recording!`,
                    files: [new MessageAttachment(`./records/audio.mp3`, 'recording.mp3')]
                });*/

                //delete both files
            //    fs.unlinkSync(`${filename}.pcm`)
              //  fs.unlinkSync(`${filename}.mp3`)
            });
        }, function (err) {
            /* handle error by sending error message to discord */
            return msg.edit(`❌ An error occurred while processing your recording: ${err.message}`);
        });
    }

    if (message.content === ">leave") {
        getVoiceConnection(message.guildId.toString()).disconnect();
    }

    await podcastFunctions(message);
});

function createListeningStream(receiver, userId, user) {
    const opusStream = receiver.subscribe(userId, {
        end: {
            behavior: EndBehaviorType.AfterSilence,
            duration: 100,
        },
    });

    const oggStream = new prism.opus.OggLogicalBitstream({
        opusHead: new prism.opus.OpusHead({
            channelCount: 2,
            sampleRate: 48000,
        }),
        pageSizeControl: {
            maxPackets: 10,
        },
    });

    let filename = "./records/audio.pcm";
    const out = fs.createWriteStream(filename, {flags: 'a'});

    console.log(`👂 Started recording ${filename}`);

    pipeline(opusStream, oggStream, out, (err) => {
        if (err) {
            console.warn(`❌ Error recording file ${filename} - ${err.message}`);
        } else {
            console.log(`✅ Recorded ${filename}`);
        }
    });
}

async function getPopularPodcasts() {
    httpGetAsync("https://api.audioboom.com/audio_clips/popular", function (res) {
    });
}

function randomPodcast() {
    let podcastToBePlayed = Math.floor((Math.random() * popularPodcasts.length) + 1);
    console.log(podcastToBePlayed);
    return podcastToBePlayed;
}

function fillPopularPodcasts(data) {
    data.body.audio_clips.forEach(currentAudio => {
        popularPodcasts.push((currentAudio.urls.high_mp3).toString());
    });
}

function httpGetAsync(theUrl, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState === 4 && xmlHttp.status === 200) {
            fillPopularPodcasts(JSON.parse(xmlHttp.responseText));
            callback(xmlHttp.responseText);
        }
    };
    xmlHttp.open("GET", theUrl, true); // true for asynchronous
    xmlHttp.send(null);
}

client.login(token);