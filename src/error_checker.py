import ast
import wx.stc
import json
import subprocess
from pathlib import Path

class BaseSyntaxChecker:
    def __init__(self, editor):
        self.editor = editor
        
    def check_syntax(self, code):
        """To be implemented by subclasses"""
        return True

class PythonChecker(BaseSyntaxChecker):
    def check_syntax(self, code):
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            return False, [{'line': e.lineno, 'message': str(e)}]
        except Exception as e:
            return False, [{'line': 0, 'message': f"General error: {str(e)}"}]

class JavaScriptChecker(BaseSyntaxChecker):
    def check_syntax(self, code):
        try:
            # First check if eslint is installed
            subprocess.run(["eslint", "--version"], 
                          check=True,
                          capture_output=True,
                          text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Install eslint locally if not found
            try:
                subprocess.run(["npm", "install", "eslint", "--save-dev"],
                              check=True,
                              capture_output=True)
            except subprocess.CalledProcessError as install_error:
                return False, [{
                    'line': 0,
                    'message': f"Failed to install ESLint: {install_error.stderr}"
                }]

        # Create temp file with the code
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as tmp:
            tmp.write(code.encode('utf-8'))
            tmp_path = tmp.name

        try:
            # If eslint cnfig isn't present, create the simplest possible config
            try:
                with open("eslint.config.js", r) as eslint_config:
                    config = eslint_config.read()
            except FileNotFoundError:
                with open("eslint.config.js", w):
                    file.write('{"rules":{"no-undef":"error","eqeqeq":"error","no-unused-vars":"warn"}}')

            # Run eslint on the temp file
            result = subprocess.run(
                ["npx", "eslint", "-f", "json", tmp_path],
                capture_output=True,
                text=True
            )
            
            errors = []
            if result.returncode == 0:
                return True, []
                
            # Parse eslint JSON output
            eslint_results = json.loads(result.stdout)
            for file in eslint_results:
                for msg in file['messages']:
                    errors.append({
                        'line': msg.get('line', 0),
                        'message': f"{msg.get('message', 'Unknown error')} [{msg.get('ruleId', '')}]"
                    })
            
            return False, errors

        except Exception as e:
            return False, [{'line': 0, 'message': f"ESLint error: {str(e)}"}]
            
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class SyntaxChecker:
    _checkers = {
        '.py': PythonChecker,
        '.js': JavaScriptChecker,
        # Add more checkers here
    }
    
    def __init__(self, editor):
        self.editor = editor
        self.current_checker = None
        
    def set_file(self, file_path):
        ext = Path(file_path).suffix.lower()
        checker_class = self._checkers.get(ext)
        self.current_checker = checker_class(self.editor) if checker_class else None
        
    def check_syntax(self, code):
        if not self.current_checker:
            return True
            
        # Clear existing markers
        self.editor.MarkerDeleteAll(1)
        
        # Setup error markers
        self.editor.MarkerDefine(1, wx.stc.STC_MARK_BACKGROUND)
        self.editor.MarkerSetBackground(1, wx.RED)
        self.editor.MarkerSetAlpha(1, 30)
        
        valid, errors = self.current_checker.check_syntax(code)
        
        for error in errors:
            if error['line']:
                self.editor.MarkerAdd(error['line'] - 1, 1)
                
        status = "No syntax errors" if valid else f"Found {len(errors)} errors"
        wx.GetTopLevelParent(self.editor).SetStatusText(f"    {status}")
        
        return valid
