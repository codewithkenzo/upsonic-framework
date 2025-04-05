# Development Process

## Git Commit Routine

To maintain clean, traceable history and ensure easy tracking of changes, we follow these guidelines for commits:

1. **Commit Frequently**:
   - Make small, focused commits after completing a logical unit of work
   - Generally commit after implementing a single feature, fixing a bug, or making significant edits

2. **Commit Message Format**:
   ```
   [area]: Short description of what changed

   More detailed explanation if needed
   ```

3. **Area Prefixes**:
   - `[core]`: Core framework functionality
   - `[agent]`: Agent-related changes
   - `[browser]`: Browser agent functionality
   - `[cli]`: Command-line interface
   - `[docs]`: Documentation updates
   - `[test]`: Test-related changes
   - `[config]`: Configuration changes
   - `[example]`: Example code updates

4. **When to Commit**:
   - After adding a new feature or method
   - After fixing a bug
   - After refactoring code
   - After updating documentation
   - Before switching to a different task

5. **Before Committing**:
   - Run the tests to ensure nothing broke
   - Check for any debug code that should be removed
   - Review the changes with `git diff`

## Development Workflow

1. **Create a Feature Branch**: 
   ```
   git checkout -b feature/short-description
   ```

2. **Work and Commit Frequently**:
   ```
   git add [files]
   git commit -m "[area]: Description"
   ```

3. **Push Changes Regularly**:
   ```
   git push origin feature/short-description
   ```

4. **Create a Pull Request** when the feature is complete

5. **Update Your Branch** before merging:
   ```
   git checkout main
   git pull
   git checkout feature/short-description
   git merge main
   git push
   ```

## Example Commit Messages

- `[core]: Add Task class with context support`
- `[agent]: Implement execute_task method for BaseAgent`
- `[browser]: Fix screenshot path generation`
- `[cli]: Add browser command to app.py`
- `[docs]: Update README with browser agent examples`
- `[test]: Add tests for browser agent` 