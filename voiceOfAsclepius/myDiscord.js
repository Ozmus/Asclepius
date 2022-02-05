const { Client, Intents } = require('discord.js');
const client = new Client({ intents: [Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]} );
const { token } = require("./config.json")
const  fs  = require("fs");
const command = require("./command");

client.on("ready", () => {
    console.log(`Logged in as ${client.user.tag}!`)
})

client.on("message", async message => {

    if (message.content === ">record") {
        await command.record(message);
    }

    if (message.content === ">stopRecord") {
        await command.stopRecording(message);
    }

});


client.login(token);