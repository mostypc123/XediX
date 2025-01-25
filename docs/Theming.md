# XediX Custom Theme Documentation

## JSON Theme Configuration

XediX supports custom themes through JSON configuration. Place your theme configuration in `theme.xcfg` to override the default themes.

### Basic Structure

```json
{
  "background": "#1B1F2B",
  "foreground": "#FFFFFF",
  "comment": "#68C147",
  "keyword": "#569CD6",
  "string": "#BA9EFE",
  "number": "#FFDD54",
  "operator": "#D4D4D4",
  "lineNumberBg": "#1B1F2B"
}
```

### Color Properties

- `background`: Main editor background color
- `foreground`: Default text color
- `comment`: Color for comments (e.g., # in Python)
- `keyword`: Color for language keywords (e.g., def, class, import)
- `string`: Color for string literals
- `number`: Color for numeric literals
- `operator`: Color for operators
- `lineNumberBg`: Background color for line number margin (defaults to background if not specified)

### Color Format
- Use hexadecimal color codes with # prefix
- Support for 6-digit hex codes (#RRGGBB)

### Example Themes

#### Dark Theme
```json
{
  "background": "#1B1F2B",
  "foreground": "#FFFFFF",
  "comment": "#68C147",
  "keyword": "#569CD6",
  "string": "#BA9EFE",
  "number": "#FFDD54",
  "operator": "#D4D4D4"
}
```

#### Light Theme
```json
{
  "background": "#FFFFFF",
  "foreground": "#000000",
  "comment": "#008000",
  "keyword": "#0000FF",
  "string": "#A31515",
  "number": "#098658",
  "operator": "#000000"
}
```

### Implementation Notes

1. The theme configuration is read when opening files
2. If JSON parsing fails, XediX falls back to built-in themes
3. Missing properties will use default values
4. Changes require reopening files to take effect

## Built-in Theme Configuration

XediX provides several built-in themes that can be configured using simple string values in `theme.xcfg`. To use a built-in theme, simply write the theme name in `theme.xcfg`.

### Available Themes

#### Dark Theme
- Name: `dark`
- Background: #1B1F2B
- Text: White
- Comments: Green
- Keywords: Blue
- Strings: Purple

#### Light Theme
- Name: `light`
- Background: White
- Text: Black
- Comments: Dark Green
- Keywords: Blue
- Strings: Dark Red

#### Night Theme
- Name: `night`
- Background: #2f3139
- Text: White
- Comments: Tan
- Keywords: Blue
- Strings: Purple

#### Obsidian Theme
- Name: `obsidian`
- Background: #212232
- Text: White
- Comments: Pink
- Keywords: Blue
- Strings: Purple

#### Solarized Themes
- Names: `solarized-light`, `solarized-dark`
- Light/dark variants of the Solarized color scheme
- Optimized for readability with careful color selection

#### GitHub Themes
- Names: `github-light`, `github-dark`, `github-dimmed`
- Official GitHub color schemes
- Matches GitHub's web interface colors

### Usage

1. Open `theme.xcfg`
2. Write just the theme name (e.g., `dark` or `github-light`)
3. Save and restart XediX

Example `theme.xcfg`:
```
dark
```