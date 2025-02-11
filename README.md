
# Xbox Crasher

This project is something I wanted to try my hand at, and I've seen other services such as Octosniff which has similar methods. I am going to expose these methods so that they may get fixed in the future. I enjoyed making this and the deployment of this may be VERY difficult unless you are very familiar with Python and backend development. This is solely for educational purposes only, and I am not responsible for what you choose to do with the application.



## Requirements

```bash
https://github.com/OpenXbox/xbox-webapi-python (Xbox Open API)
https://github.com/Rapptz/discord.py (Discord.py)
https://github.com/OpenXbox/ms_cv (ms_cv)
```
I suggest having a virtual environment for this project. Additionally, I used a forked and modified version of Xbox Open API for SISU refresh codes, you may want to modifiy the code accordingly.


## Deployment

To run the project, simply run

```bash
  python main.py
```
once you have the dependencies installed.


## Contributing

Contributions are always welcome!



## Optimizations

The code provided is extremely unoptimized, and performance may vary


## Documentation

I primarily open-sourced this project to allow others to modify it according to their needs. The main goal is to interact with Discord, triggering API calls that can cause crashes within the platform. To ensure the commands appear in your server, you'll need to sync them with the specific Discord guild where you invite the bot. This process is straightforward for detailed guidance, please refer to the [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/).

#### Main commands/features:

- CreateLFG `Creates a looking for group post using the target game`
- Link Account `"Links account with microsoft`
- Unlink Account `Not implemented`
- Joinstate `Make party open or closed`
- Crash Party `Crashes target's party`
- Crash Loop `Crashes targets party until given timeframe`
- Spam Invite `Spam invites a target gamertag`
- Send Message `Send target a message`
- Anti Kick `Makes you unkickable`
## License

MIT License

Copyright (c) 2025 SAT727

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
