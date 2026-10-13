# B1 - exact broker policy changes

User-approved wording from the 13 October 2026 instruction. The three active
rule sources were searched case-insensitively for broker/connectivity language.
The order-placement restrictions in CLAUDE.md D9 and the blueprint's execution
sections remain: this task authorizes only market-data connectivity.

| File | Old text | Replacement / addition |
|---|---|---|
| docs/desk/TRADING_BLUEPRINT.md, Praman amendment 5 | Broker-API order placement is a separate task that needs explicit approval, including a compliance check against SEBI's framework for retail algorithmic trading. Until then there is no broker connectivity of any kind. | Broker connectivity is limited to read-only market data from Angel One SmartAPI. Praman may only log in and out, read the profile, fetch quotes and candle data, stream the market feed and download the public scrip master. No order, GTT, position, holdings or funds calls. Angel's key can technically place orders, so this is enforced in code. Credentials never enter the repository, logs, test fixtures or any chat: the API key comes from the environment variable ANGEL_API_KEY, and the client ID, PIN and TOTP are typed by me at runtime and kept only in memory. The forward-window firewall applies to this data. Placing orders still needs a separate, approved task with a SEBI compliance check. |
| CLAUDE.md | No blanket broker-connectivity prohibition existed. D9 forbids order placement and is retained. | Added: Broker connectivity is limited to read-only market data from Angel One SmartAPI. Praman may only log in and out, read the profile, fetch quotes and candle data, stream the market feed and download the public scrip master. No order, GTT, position, holdings or funds calls. Angel's key can technically place orders, so this is enforced in code. Credentials never enter the repository, logs, test fixtures or any chat: the API key comes from the environment variable ANGEL_API_KEY, and the client ID, PIN and TOTP are typed by me at runtime and kept only in memory. The forward-window firewall applies to this data. Placing orders still needs a separate, approved task with a SEBI compliance check. |
| AGENTS.md | No broker-connectivity text existed. | Added: Broker connectivity is limited to read-only market data from Angel One SmartAPI. Praman may only log in and out, read the profile, fetch quotes and candle data, stream the market feed and download the public scrip master. No order, GTT, position, holdings or funds calls. Angel's key can technically place orders, so this is enforced in code. Credentials never enter the repository, logs, test fixtures or any chat: the API key comes from the environment variable ANGEL_API_KEY, and the client ID, PIN and TOTP are typed by me at runtime and kept only in memory. The forward-window firewall applies to this data. Placing orders still needs a separate, approved task with a SEBI compliance check. |

The blueprint's conditional prohibitions on unapproved broker automation are
order-automation rules, not a prohibition on the explicitly approved read-only
connection; they remain binding. No frozen pre-registration, rulebook or pinned
research pipeline was edited.
