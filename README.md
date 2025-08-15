# YeetBot
A bot for the Yeet Discord Server

Hey, this is a personal bot I'm mainly using for my Discord and Minecraft server, to combine functionality between them, however it also has some other features. Many values are stored via config to persist through bot lifetimes. Feel free to change things to get them to work for your server.

## Minecraft Server Cog

- /start                 => Remotely starts the currently selected server (User must have minecraft permission discord role)
- /stop                  => Remotely stops whichever server is currently running
- /restart               => Stops the current server, and starts the currently selected server (most often, this is going to be the same selection)
- /server                => "-" parameter displays current selected server, otherwise, server dropdown changes selected server
- /ping                  => Bot will respond "Pong" to ensure bot is online
- /status                => Will give the status of the server, if one is up or not
- /list                  => Runs the /list command in minecraft, and prints the result
- /tps                   => Runs /forge tps or /neoforge tps to get server performance values
- /say <message>         => Says the message in chat as [Rcon]

## Snoopie Fact Cog

- /snoopiefact           => Sends a snapple style fact to whichever discord server the command was sent in
- /gemini                => Uses gemini API to ask a question to the AI
- /sendallsnoopiefact    => Sends a snapple style fact to every discord server the bot is in that has a valid channel (Locked to bot admins - which is only me at the moment)
Automatically sends a sendallsnoopiefact every day at 10am - as long as the bot is running

## Role/Channel Setting Cog

- /setmcpermsrole        => Set the role that can use the minecraft commands
- /setmcconsolepermsrole => Set the role that can use the minecraft console commands
- /setmcconsolechannel   => Set the channel for Minecraft console messages
- /setmcchatchannel      => Set the channel for Minecraft chat messages
- /setmcbotchannel       => Set the channel for the Minecraft bot messages
- /setfactchannel        => Set the channel for Snoopie facts
- /setfactrole           => Set the role to ping for Snoopie facts
- /setpermsrole          => Set the role to have Snoopie fact permissions

Questions can be brought to timothy.kwartler@gmail.com