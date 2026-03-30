from __future__ import annotations

OFFICIAL_SOURCES = {
    "openai": "https://platform.openai.com/docs/",
    "github": "https://docs.github.com/",
    "gitlab": "https://docs.gitlab.com/",
    "docker": "https://docs.docker.com/",
    "kubernetes": "https://kubernetes.io/docs/",
    "terraform": "https://developer.hashicorp.com/terraform/docs",
    "aws": "https://docs.aws.amazon.com/",
    "azure": "https://learn.microsoft.com/azure/",
    "gcp": "https://cloud.google.com/docs",
    "python": "https://docs.python.org/3/",
}

TOOL_KEYWORDS = {
    "openai": ["openai", "gpt", "responses api", "assistants", "agent"],
    "github": ["github", "actions", "repository", "pull request"],
    "gitlab": ["gitlab", "gitlab ci"],
    "docker": ["docker", "container", "dockerfile"],
    "kubernetes": ["kubernetes", "k8s", "helm", "kubectl"],
    "terraform": ["terraform", "iac", "hcl"],
    "aws": ["aws", "ec2", "s3", "lambda", "eks", "iam"],
    "azure": ["azure", "aks", "bicep", "entra"],
    "gcp": ["gcp", "gke", "bigquery", "vertex ai"],
    "python": ["python", "fastapi", "django", "pandas"],
}
