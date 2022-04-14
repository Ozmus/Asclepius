const {entersState, joinVoiceChannel, VoiceConnectionStatus, EndBehaviorType} = require('@discordjs/voice');
const {createWriteStream} = require('node:fs');
const prism = require('prism-media');
const {pipeline} = require('node:stream');
const {Client, Intents, MessageAttachment, Collection} = require('discord.js');
const ffmpeg = require('ffmpeg');
const sleep = require('util').promisify(setTimeout);
const fs = require('fs');
const {token} = require("./config.json");

/* Initialize Discord Client */
const client = new Client({
    intents: [
        Intents.FLAGS.GUILDS,
        Intents.FLAGS.GUILD_MESSAGES,
        Intents.FLAGS.GUILD_MEMBERS,
        Intents.FLAGS.GUILD_VOICE_STATES
    ]
})

/* Collection to store voice state */
client.voiceManager = new Collection()

/* Ready event */
client.on("ready", () => {
    console.log("Connected as", client.user.tag, "to discord!");
})

/* When message is sent*/
client.on('messageCreate', async (message) => {
    /* If content starts with `!record` */
    if (message.content.startsWith('!record')) {
        /* If member do not have admin perms */
        if (!message.member.permissions.has('ADMINISTRATOR')) return message.channel.send('You do not have permission to use this command.');
        /* Get the voice channel the user is in */
        const voiceChannel = message.member.voice.channel
        /* Check if the bot is in voice channel */
        let connection = client.voiceManager.get(message.channel.guild.id)

        /* If the bot is not in voice channel */
        if (!connection) {
            /* if user is not in any voice channel then return the error message */
            if (!voiceChannel) return message.channel.send("You must be in a voice channel to use this command!")

            /* Join voice channel*/
            connection = joinVoiceChannel({
                channelId: voiceChannel.id,
                guildId: voiceChannel.guild.id,
                selfDeaf: false,
                selfMute: true,
                adapterCreator: voiceChannel.guild.voiceAdapterCreator,
            });

            /* Add voice state to collection */
            client.voiceManager.set(message.channel.guild.id, connection);
            await entersState(connection, VoiceConnectionStatus.Ready, 20e3);
            const receiver = connection.receiver;

            /* When user speaks in vc*/
            receiver.speaking.on('start', (userId) => {
                if (userId !== message.author.id) return;
                /* create live stream to save audio */
                createListeningStream(receiver, userId, client.users.cache.get(userId));
            });

            /* Return success message */
            return message.channel.send(`🎙️ I am now recording ${voiceChannel.name}`);

            /* If the bot is in voice channel */
        } else if (connection) {
            /* Send waiting message */
            const msg = await message.channel.send("Please wait while I am preparing your recording...")
            /* wait for 5 seconds */
            await sleep(5000)

            /* disconnect the bot from voice channel */
            connection.destroy();

            /* Remove voice state from collection */
            client.voiceManager.delete(message.channel.guild.id)

            const filename = `./records/${message.author.id}`;

            /* Create ffmpeg command to convert pcm to mp3 */
            const process = new ffmpeg(`${filename}.pcm`);
            process.then(function (audio) {
                audio.fnExtractSoundToMP3(`${filename}.mp3`, async function (error, file) {
                    //edit message with recording as attachment
                    await msg.edit({
                        content: `🔉 Here is your recording!`,
                        files: [new MessageAttachment(`./records/${message.author.id}.mp3`, 'recording.mp3')]
                    });

                    //delete both files
                    fs.unlinkSync(`${filename}.pcm`)
                    fs.unlinkSync(`${filename}.mp3`)
                });
            }, function (err) {
                /* handle error by sending error message to discord */
                return msg.edit(`❌ An error occurred while processing your recording: ${err.message}`);
            });

        }
    }
})


client.login("BOT TOKEN")


//------------------------- F U N C T I O N S ----------------------//

/* Function to write audio to file (from discord.js example) */
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

    const filename = `./records/${user.id}.pcm`;
    const out = createWriteStream(filename, { flags: 'a' });
    console.log(`👂 Started recording ${filename}`);

    pipeline(opusStream, oggStream, out, (err) => {
        if (err) {
            console.warn(`❌ Error recording file ${filename} - ${err.message}`);
        } else {
            console.log(`✅ Recorded ${filename}`);
        }
    });
}

client.login("OTU3NjU4NjM4NDI2NzEwMDM2.YkB_Gw.KKCNVbHBMU6jmzQV5pvqMc8We5w");