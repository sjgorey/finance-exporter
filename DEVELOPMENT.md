# Development Workflow

This document outlines the recommended development workflow for the finance-exporter project.

## Git Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test locally:
   ```bash
   # Test the application
   python finance_exporter.py
   
   # Build and test Docker image
   docker build -t finance-exporter-test .
   docker run -p 8080:8080 finance-exporter-test
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push feature branch**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

5. **Create Pull Request** on GitHub

6. **After merge, clean up**:
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/your-feature-name
   ```

### Hotfix Workflow

For urgent production fixes:

1. **Create hotfix branch from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/issue-description
   ```

2. **Make fix and test**

3. **Commit and push**:
   ```bash
   git commit -m "fix: urgent issue description"
   git push -u origin hotfix/issue-description
   ```

4. **Create PR for immediate merge**

## Release Workflow

### Creating a Release

1. **Update version in relevant files** (if applicable)

2. **Create release branch**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/v1.0.0
   ```

3. **Build and test Docker image**:
   ```bash
   docker build -t sjgorey/finance-exporter:v1.0.0 .
   docker build -t sjgorey/finance-exporter:latest .
   ```

4. **Test thoroughly**

5. **Commit release**:
   ```bash
   git commit -m "release: v1.0.0"
   git push -u origin release/v1.0.0
   ```

6. **Create PR to main**

7. **After merge, create Git tag**:
   ```bash
   git checkout main
   git pull origin main
   git tag v1.0.0
   git push origin v1.0.0
   ```

8. **Push Docker images**:
   ```bash
   docker push sjgorey/finance-exporter:v1.0.0
   docker push sjgorey/finance-exporter:latest
   ```

9. **Create GitHub Release** with release notes

## Useful Commands

### Daily Development

```bash
# Check status
git status

# See recent commits
git log --oneline -10

# Check differences
git diff

# Pull latest changes
git pull origin main

# Push current branch
git push
```

### Docker Operations

```bash
# Build image
docker build -t sjgorey/finance-exporter:latest .

# Run locally
docker run -p 8080:8080 sjgorey/finance-exporter:latest

# Run with custom config
docker run -p 8080:8080 \
  -e SYMBOLS="AAPL,GOOGL" \
  -e UPDATE_INTERVAL=60 \
  sjgorey/finance-exporter:latest

# Push to registry
docker push sjgorey/finance-exporter:latest

# Clean up local images
docker image prune
```

### Repository Management

```bash
# Add new remote (if needed)
git remote add upstream https://github.com/original/repo.git

# View remotes
git remote -v

# Fetch all branches
git fetch --all

# List all branches
git branch -a
```

## Commit Message Convention

Use conventional commit messages:

- `feat:` - New features
- `fix:` - Bug fixes  
- `docs:` - Documentation updates
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Example: `feat: add support for crypto symbols`

## GitHub Integration

### Setting up GitHub Actions (Optional)

You can add automated testing and building with GitHub Actions by creating `.github/workflows/ci.yml`.

### Issues and Pull Requests

- Use GitHub Issues to track bugs and feature requests
- Reference issues in commit messages: `fix: resolve symbol parsing issue (#12)`
- Use descriptive PR titles and descriptions
- Request reviews from team members