# envault

> A local secrets manager that encrypts and syncs `.env` files across projects using a master passphrase.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Encrypt and store your `.env` file:**

```bash
envault lock --file .env
```

**Decrypt and restore your `.env` file:**

```bash
envault unlock --file .env
```

**List all stored vaults:**

```bash
envault list
```

**Sync secrets to another project:**

```bash
envault sync --from ./project-a --to ./project-b
```

You will be prompted for your master passphrase on each operation. Encrypted secrets are stored in `~/.envault/` and never committed to version control.

> **Tip:** Add `.env` to your `.gitignore` and commit only the `.env.vault` reference file.

---

## How It Works

envault uses AES-256 encryption (via the `cryptography` library) to encrypt your `.env` files locally. A single master passphrase is used to derive an encryption key, keeping your secrets safe at rest while making them easy to share across machines or projects.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)
