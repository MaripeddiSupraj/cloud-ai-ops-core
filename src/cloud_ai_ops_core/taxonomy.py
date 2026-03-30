from __future__ import annotations

CATEGORY_KEYWORDS = {
    "ai": ["ai", "llm", "gpt", "agent", "rag", "prompt", "genai"],
    "cloud": ["cloud", "aws", "azure", "gcp", "saas"],
    "devops": ["devops", "cicd", "pipeline", "deployment", "sre", "platform engineering"],
    "kubernetes": ["kubernetes", "k8s", "helm", "kubectl", "cluster"],
    "security": ["security", "iam", "compliance", "vulnerability", "secrets"],
    "engineering": ["engineering", "architecture", "backend", "frontend", "api", "system design"],
}

TOOL_KEYWORDS = {
    "github": ["github", "actions", "pull request", "repository", "repo"],
    "gitlab": ["gitlab", "gitlab ci", "gitlab-ci"],
    "docker": ["docker", "dockerfile", "container"],
    "kubernetes": ["kubernetes", "k8s", "kubectl", "helm"],
    "terraform": ["terraform", "iac", "hcl"],
    "aws": ["aws", "ec2", "s3", "lambda", "eks"],
    "azure": ["azure", "aks", "arm"],
    "gcp": ["gcp", "gke", "bigquery"],
    "python": ["python", "fastapi", "django", "pandas"],
    "openai": ["openai", "gpt", "assistants", "responses api"],
}

OFFICIAL_SOURCES = {
    "github": ["https://docs.github.com/"],
    "gitlab": ["https://docs.gitlab.com/"],
    "docker": ["https://docs.docker.com/"],
    "kubernetes": ["https://kubernetes.io/docs/"],
    "terraform": ["https://developer.hashicorp.com/terraform/docs"],
    "aws": ["https://docs.aws.amazon.com/"],
    "azure": ["https://learn.microsoft.com/azure/"],
    "gcp": ["https://cloud.google.com/docs"],
    "python": ["https://docs.python.org/3/"],
    "openai": ["https://platform.openai.com/docs/"],
    "ai": ["https://platform.openai.com/docs/"],
    "cloud": ["https://docs.aws.amazon.com/", "https://learn.microsoft.com/azure/", "https://cloud.google.com/docs"],
    "devops": ["https://docs.github.com/actions", "https://docs.gitlab.com/ee/ci/"],
    "security": ["https://owasp.org/www-project-top-ten/"],
}

