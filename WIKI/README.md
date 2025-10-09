# Info

the project is sepparated in two files, client and server:

- [CLIENT](https://github.com/IanSouzaFreire/Forca-G/blob/Wiki/WIKI/CLIENT.md):
  > Written in HTML5 an JQuery, makes calls to the server's API for payment and resources.


- [SERVER](https://github.com/IanSouzaFreire/Forca-G/blob/Wiki/WIKI/SERVER.md):
  > Written in Python with FLask, stores data and sends it to clients.

# How it works:

Basic understanding of functionality: <br />
→ Client sends POST /payout with json → <br />
→ Server: <br />
   ├── Calculates pricing <br />
   ├── Generates BRCode <br />
   ├── Creates QR code PNG <br />
   ├── Server sends data needed <br />
→ Client: <br />
   ├── Receive two segments of data <br />
   ├── See if QRcode is usable <br />
   ├── render QRcode along with other payment info <br />
→ When payment is confirmed: <br />
   ├── Server checks user's posts <br />
   ├── return data collected to the Client <br />
