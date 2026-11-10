# Snaketriage

[Snakemake](https://github.com/snakemake/) is a powerful and versatile workflow manager for all kinds of data processing tasks.
However, over the past years a considerable backlog of open but potentially outdated, duplicated, or highly connected issues have accumulated.

The purpose of this project is to implement a triage workflow that watches the [public Snakemake issues](https://github.com/snakemake/snakemake/issues), groups issues by topic, and ranks the resulting clusters by relevance.

The goal is also to flag issues/meta-issues that are potentially outdated and superseded by the current code-base, and suggest those for closing or quick fixes.

## Current scope

The tool can be run locally or as a Github action.
Briefly, it consists of the following steps:

1. Fetch open issues from the Snakemake GitHub repository.
2. Embed issue text using a sentence-transformer model.
3. Cluster issues by similarity into meta-issues, identify overarching topics
4. Post-processing: Rank meta-issues by relevance (code impact, criticality, age)
5. Render results as a static web page, served on [GitHub.io](https://mpusp.github.io/snaketriage)

## Project layout

- `src/snaketriage/cli.py` — Main entrypoint for `snaketriage`
- `src/snaketriage/fetch_issues.py` — Fetches open issues from GitHub
- `src/snaketriage/embedding.py` — Creates text embeddings for downloaded issues
- `data/raw/` — raw issue dumps
- `data/models/` — downloaded sentence-transformer models
- `data/embeddings/` — serialized embeddings and metadata

## Setup

This project is managed by pixi for dependencies and tasks.
The tool can be run and tested using pixi tasks, it can be installed via PyPi, or in the most usual case, run via GitHub Actions which will render and deploy a static website.

### GitHub

```bash
# fetch latest version of the repository from GitHub
git clone https://github.com/MPUSP/snaketriage.git
cd snaketriage

# create and activate virtual environment for pixi
pixi install
pixi shell

# run dedicated tasks
pixi run test_repo
```

### PyPi

- TODO: Installation instructions for PyPi to be added once it is released

## Fetch and embed issues

This will query the GitHub Issues API and save open issues (excluding pull requests) as JSON lines.

```bash
python src/snaketriage/cli.py \
  --owner MPUSP \
  --repo intranet \
  --limit 100
```

## Environment

For authenticated reads against the GitHub API (higher rate limit), export your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN=<your_token_here>
```

## Authors

- Dr. Michael Jahn
  - Affiliation: [Max-Planck-Unit for the Science of Pathogens](https://www.mpusp.mpg.de/) (MPUSP), Berlin, Germany
  - ORCID profile: https://orcid.org/0000-0002-3913-153X
  - github page: https://github.com/m-jahn

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.