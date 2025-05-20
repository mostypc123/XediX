import ast
import wx.stc


class SyntaxChecker:
    def __init__(self, editor):
        self.editor = editor

    def check_syntax(self):
        """Check Python syntax and mark errors if found."""
        code = self.editor.GetText()
        if not code.strip():
            return True

        # Clear any existing error markers
        self.editor.MarkerDeleteAll(1)

        # Setup error marker style
        self.editor.MarkerDefine(1, wx.stc.STC_MARK_BACKGROUND)
        self.editor.MarkerSetBackground(1, wx.RED)
        self.editor.MarkerSetAlpha(1, 30)

        try:
            # First try parsing the whole file
            ast.parse(code)
            wx.GetTopLevelParent(self.editor).SetStatusText("    No syntax errors")
            return True

        except SyntaxError as e:
            # If we have line info, mark that specific line
            if e.lineno:
                self.editor.MarkerAdd(e.lineno - 1, 1)
                wx.GetTopLevelParent(self.editor).SetStatusText(
                    f"    Syntax error on line {e.lineno}: {str(e)}"
                )
            else:
                # If no line info, try to find the first invalid line
                lines = code.split("\n")
                for i, line in enumerate(lines):
                    try:
                        if line.strip():  # Only check non-empty lines
                            ast.parse(line)
                    except SyntaxError:
                        self.editor.MarkerAdd(i, 1)
                        wx.GetTopLevelParent(self.editor).SetStatusText(
                            f"    Syntax error on line {i + 1}: Invalid syntax"
                        )
                        break
            return False

        except Exception as e:
            wx.GetTopLevelParent(self.editor).SetStatusText(
                f"    Error checking syntax: {str(e)}"
            )
            # Try to find invalid lines
            lines = code.split("\n")
            for i, line in enumerate(lines):
                try:
                    if line.strip() and not line.strip().startswith("#"):
                        ast.parse(line)
                except SyntaxError:
                    self.editor.MarkerAdd(i, 1)
            return False
