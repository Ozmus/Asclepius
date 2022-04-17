const {Client, Intents} = require('discord.js');
const client = new Client({intents: [Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]});
const {token} = require("./config.json")
const fs = require("fs");

client.on("ready", () => {
    console.log(`Logged in as ${client.user.tag}!`)
})

var inputStream;
var outputStream;

client.on("message", async message => {

    if (message.content === ">record") {

        var fileName = __dirname+ "/records/merge.pcm";
        outputStream = fs.createWriteStream(fileName);
        const voiceChannelId = message.member.voice.channel.id;
        if (voiceChannelId == null) {
            message.channel.send("Please join a channel.");
        } else {
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
        const { channel: voiceChannel } = message.guild.voiceStates.cache.last();
        voiceChannel.leave();
        let filePath = __dirname + "/" + message.member.id;
        const chunks = fs.readdirSync(filePath);
        mergePCM(chunks,filePath);
    }

});

function mergePCM(chunks,filePath) {

    if (chunks.length == 0) {
        fs.rmdirSync(filePath, {recursive: true});
        return;
    }

    let currentfile = filePath + "/" + chunks.shift();
    inputStream = fs.createReadStream(currentfile);
    inputStream.pipe(outputStream, { end: false });

    inputStream.on('end', function() {
        mergePCM(chunks, filePath);
    });
}

client.login(token);