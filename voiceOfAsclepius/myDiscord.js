const { Client, Intents } = require('discord.js');
const client = new Client({ intents: [Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]} );
const { token } = require("./config.json")
const  fs  = require("fs");

client.on("ready", () => {
    console.log(`Logged in as ${client.user.tag}!`)
})

client.on("message", async message => {

    if (message.content === ">record") {
            const voiceChannelId = message.member.voice.channel.id;
            const voiceChannel = message.guild.channels.cache.get(voiceChannelId);
            await voiceChannel.join().then(
                conn => {
                    let reciever = conn.receiver;
                    conn.on('speaking', (user, speaking) => {
                        if (speaking) {
                            const audioStream = reciever.createStream(user, {mode: 'pcm'});
                            const memberDirectory = __dirname+"/"+message.member.id;
                            if(!fs.existsSync(memberDirectory)) {
                                fs.mkdirSync(memberDirectory, {
                                    recursive : true
                                });
                            }
                            let filePath = memberDirectory + "/" + Date.now() + ".pcm";
                            audioStream.pipe(fs.createWriteStream(filePath));
                        }
                    });
                }
            ).catch(
                err => { throw err; }
            );
    }

    if (message.content === ">stopRecord") {
        const { channel: voiceChannel } = message.guild.voiceStates.cache.last();
        voiceChannel.leave();
        let filePath = __dirname + "/" + message.member.id;
        const chunks = fs.readdirSync(filePath);
        mergePCM(chunks,filePath);
    }

});

var inputStream;
var fileName = __dirname+ "/records/merge" + Date.now() + ".pcm";
const outputStream = fs.createWriteStream(fileName);

function mergePCM(chunks,filePath) {

    if (chunks.length == 0) {
        fs.rm(filePath, {recursive: true});
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