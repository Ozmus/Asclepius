const {Client, Intents} = require('discord.js');
const client = new Client({intents: [Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]});
const {
    joinVoiceChannel,
    createAudioPlayer,
    createAudioResource,
    AudioPlayerStatus,
    VoiceConnectionStatus,
    entersState
} = require('@discordjs/voice');
const {token} = require("./config.json")
const fs = require("fs");
var XMLHttpRequest = require('xhr2');

const popularPodcasts = [];
const player = createAudioPlayer();

client.on("ready", async () => {
    console.log(`Logged in as ${client.user.tag}!`);
    await getPopularPodcasts();
})

var inputStream;
var outputStream;

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
    if (message.content === ">record") {

        var fileName = __dirname + "/records/merge.pcm";
        outputStream = fs.createWriteStream(fileName);

        if (message.member.voice.channel == null) {
            message.channel.send("Please join a channel.");
        } else {
            const voiceChannelId = message.member.voice.channel.id;
            const voiceChannel = message.guild.channels.cache.get(voiceChannelId);
            await voiceChannel.join().then(
                conn => {
                    let reciever = conn.receiver;
                    conn.on('speaking', (user, speaking) => {
                        if (speaking) {
                            const audioStream = reciever.createStream(user, {mode: 'pcm'});
                            const memberDirectory = __dirname + "/" + message.member.id;
                            if (!fs.existsSync(memberDirectory)) {
                                fs.mkdirSync(memberDirectory, {
                                    recursive: true
                                });
                            }
                            let filePath = memberDirectory + "/" + Date.now() + ".pcm";
                            audioStream.pipe(fs.createWriteStream(filePath));
                        }

                    });

                }
            ).catch(
                err => {
                    throw err;
                }
            );
        }
    }

    if (message.content === ">stopRecord") {
        const {channel: voiceChannel} = message.guild.voiceStates.cache.last();
        voiceChannel.leave();
        let filePath = __dirname + "/" + message.member.id;
        const chunks = fs.readdirSync(filePath);
        mergePCM(chunks, filePath);
    }

    if (message.content === ">leave") {
        const voiceChannelId = message.member.voice.channel.id;
        const voiceChannel = message.guild.channels.cache.get(voiceChannelId);
        voiceChannel.leave();
    }

    await podcastFunctions(message);
});

async function getPopularPodcasts() {
    httpGetAsync("https://api.audioboom.com/audio_clips/popular", function (res) {
    });
}

function mergePCM(chunks, filePath) {
    if (chunks.length == 0) {
        fs.rmdirSync(filePath, {recursive: true});
        return;
    }

    let currentfile = filePath + "/" + chunks.shift();
    inputStream = fs.createReadStream(currentfile);
    inputStream.pipe(outputStream, {end: false});

    inputStream.on('end', function () {
        mergePCM(chunks, filePath);
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