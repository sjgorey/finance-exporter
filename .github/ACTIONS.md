# GitHub Actions Setup

This document explains how to set up GitHub Actions for automatic Docker image building and publishing.

## Required Secrets

Before the workflow can run successfully, you need to add the following secrets to your GitHub repository:

### Setting up Docker Hub Secrets

1. Go to your repository on GitHub: `https://github.com/sjgorey/finance-exporter`
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** and add:

#### DOCKER_USERNAME
- **Name**: `DOCKER_USERNAME`
- **Value**: Your Docker Hub username (e.g., `sjgorey`)

#### DOCKER_PASSWORD
- **Name**: `DOCKER_PASSWORD`  
- **Value**: Your Docker Hub access token (recommended) or password

### Creating a Docker Hub Access Token (Recommended)

Instead of using your password, create an access token:

1. Log in to [Docker Hub](https://hub.docker.com)
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. Give it a name: `github-actions-finance-exporter`
5. Select permissions: **Read & Write**
6. Copy the generated token
7. Use this token as the `DOCKER_PASSWORD` secret value

## Workflow Features

The GitHub Actions workflow (`build-and-push.yml`) includes:

### Triggers
- **Push to main**: Builds and pushes new image with `latest` tag
- **Push tags**: Builds versioned releases (e.g., `v1.0.0`)
- **Pull requests**: Runs tests only (no push)

### Testing Stage
- Python syntax checking
- Dependency installation test
- Optional linting with flake8

### Build and Push Stage
- Multi-platform builds (AMD64 and ARM64)
- Automatic tagging based on Git refs
- Docker layer caching for faster builds
- Build attestation for security

### Generated Tags

The workflow automatically creates these Docker image tags:

| Trigger | Tags Generated |
|---------|----------------|
| Push to main | `latest`, `main-<sha>` |
| Tag `v1.0.0` | `v1.0.0`, `1.0`, `1`, `latest` |
| PR #123 | `pr-123` (test build only, not pushed) |

## Manual Workflow Trigger

You can also manually trigger the workflow:

1. Go to **Actions** tab in your GitHub repository
2. Select **Build and Push Docker Image** workflow
3. Click **Run workflow**
4. Choose the branch and click **Run workflow**

## Monitoring Builds

### View Build Status
- Go to the **Actions** tab in your repository
- Click on any workflow run to see detailed logs
- Check the **Jobs** section for test and build results

### Build Badges

Add a build status badge to your README:

```markdown
![Build Status](https://github.com/sjgorey/finance-exporter/actions/workflows/build-and-push.yml/badge.svg)
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are correct
   - If using 2FA, ensure you're using an access token, not your password

2. **Build Fails**
   - Check the build logs in the Actions tab
   - Verify Dockerfile syntax
   - Ensure all dependencies in requirements.txt are valid

3. **Multi-platform Build Issues**
   - The workflow builds for both AMD64 and ARM64
   - Some Python packages may not support ARM64
   - You can remove `linux/arm64` from platforms if needed

### Debugging Steps

1. **Check workflow file syntax**:
   ```bash
   # Install GitHub CLI (if not already installed)
   gh workflow view build-and-push.yml
   ```

2. **Test Docker build locally**:
   ```bash
   docker build -t test-finance-exporter .
   ```

3. **Test multi-platform build**:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 -t test .
   ```

## Security Considerations

- **Use access tokens** instead of passwords for Docker Hub
- **Limit token permissions** to only what's needed (Read & Write for public repos)
- **Rotate tokens periodically** for security
- **Monitor workflow runs** for any suspicious activity

## Customization

### Modify Build Platforms

Edit the workflow file to change supported platforms:

```yaml
platforms: linux/amd64  # Remove ARM64 if needed
```

### Add Additional Tests

Add more testing steps in the `test` job:

```yaml
- name: Run unit tests
  run: |
    pip install pytest
    pytest tests/
```

### Custom Tagging

Modify the metadata section for different tagging strategies:

```yaml
tags: |
  type=raw,value=latest,enable={{is_default_branch}}
  type=sha,prefix=main-
  type=ref,event=branch,prefix=branch-
```