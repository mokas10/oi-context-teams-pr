# Contributing

To onboard a new team, please use the [Allen plugin](https://allen.ingka.com/get-access/context-onboarding). After onboarding, a [team resource](docs/team-resource.md) will be created for your team. Also, your team will be added as CODEOWNERS for this resource.

## Branches

The repository consists of two branches:

- `main` holds all configuration and will be tested against a Context development environment, to ensure the functionality of team resources.
- `prod` is synced with the Context production deployments in GCP EU and Alicloud CN. Any changes added to this branch will be available in Context itself within a few minutes.

## Changes

After opening a Pull Request to the `main` branch to update an existing team resource, multiple tests will be run.

- `Prettier` and `yamllint` will verify the formatting of changes
- Changes made will be validified. If changes are not valid the pull request will be automatically blocked from merging. Valid changes are documented in the [docs directory](docs/) of this repository.

A Pull Request can be approved by the owning team, if specified in the CODEOWNERS file, or will be approved by the Context team if no other team is specified. After approval and successful tests, the changes can be merged to the `main` branch. All other deployments happen automatically.
