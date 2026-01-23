# Nemo Integration

This provides a context menu for the [Nemo](https://github.com/linuxmint/nemo) file manager (default in Cinnamon), allowing you to right-click files and select **Clean Metadata**.

## Installation

### Global (All users)
Copy `mat2.nemo_action` to `/usr/share/nemo/actions/`.

```bash
sudo cp mat2.nemo_action /usr/share/nemo/actions/
```

### Local (Current user)
Copy `mat2.nemo_action` to `~/.local/share/nemo/actions/`.

```bash
mkdir -p ~/.local/share/nemo/actions/
cp mat2.nemo_action ~/.local/share/nemo/actions/
```
