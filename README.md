# Discord Bot '오디스 (Ordis)'

> Discord Bot for Warframe Community

## IMPORTANT NOTICE

- This bot is an **UNOFFICIAL** project created by a fan of Warframe.
- This bot is a privately developed bot and not affiliated with, endorsed, sponsored, or officially approved by Digital
  Extremes Ltd.
- Images and content used in this service are for informational purposes only, with no intent to infringe on copyright.
- This service is **non-commercial** and operated **FREE** of charge.

## Top Features

### Core Features for Warframe

- Real-time notifications for new in-game content (API)
- Simple commands to check real-time in-game content (Cached API data)
- Item price lookup on [Warframe.market](https://warframe.market) (API)

### And More Useful Tools & Management Systems

- Party recruitment system
- Trade system (Warframe items only)
- Admin contact system (Contact Us)
- Voice activity logging system (who, when, how long)

## Links

- 📖 [Documentation](https://wfbot-manual.farmbera.com/manual) (You can check screenshot here)
- 📜 [Terms of Service](https://wfbot-manual.farmbera.com/tos)
- 🔒 [Privacy Policy](https://wfbot-manual.farmbera.com/privacy)

## Tech Stack

| Category           | Technologies                      |
|--------------------|-----------------------------------|
| Bot                | Python                            |
| Documentation Site | TypeScript, React                 |
| Database           | MariaDB                           |
| External API       | Warframe API, Warframe.market API |
| Infra              | Self-hosted Server                |

### Key Python Libraries

| Library      | Description                                          |
|--------------|------------------------------------------------------|
| `discord.py` | Discord Bot framework                                |
| `aiomysql`   | Async MariaDB connector for non-blocking DB access   |
| `orjson`     | High-performance JSON parsing (faster than built-in) |
| `aiofiles`   | Async file I/O to avoid blocking the event loop      |
| `httpx`      | Asynchronous API caller                              |

### Directory Structure

| Directory       | Description                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------|
| api_cache/      | [Hidden] API cache                                                                                |
| config/         | [Partially Hidden] Configuration file located like general config, runtime setting, private token | 
| data/           | [Hidden] Static lookup tables for translating API codes                                           |
| docs/           | [Hidden] Markdown files served as bot help/patch notes etc.                                       |
| img/            | `.webp` images attached to embed notifications                                                    |
| locale/         | UI string translations (YAML)                                                                     |
| src/            | Bot core codes                                                                                    |
| ㄴ`src/client`   | Overall Structure of the Bot                                                                      |
| ㄴ`src/cogs`     | List of Slash Commands and Registration Methods                                                   |
| ㄴ`src/commands` | Legacy slash commands                                                                             |
| ㄴ`src/handler`  | Change-detection logic for specific content types                                                 |
| ㄴ`src/parser`   | Convert JSON data received via API into text or a Discord Embed                                   |
| ㄴ`src/services` | Business logic for party, trade, channel, warn systems                                            |
| ㄴ`src/views`    | Discord UI persistent views (buttons/modals)                                                      |
| ㄴ`src/utils`    | Shared utilities (API requests, file I/O, formatting, permissions)                                |                                                          |

### Architecture Diagram

## Copyright

© 2025. FarmBera All rights reserved.

- FarmBera holds the copyright to the source code and original content of the "오디스 (Ordis)" bot.
- Warframe and related logos, images, game data, and proper nouns are the property of Digital Extremes Ltd., and all rights to such content are reserved by Digital Extremes Ltd.
- The '오디스 (Ordis)' bot is a fan-made bot and is not affiliated with, endorsed by, sponsored by, or officially approved by Digital Extremes Ltd.
