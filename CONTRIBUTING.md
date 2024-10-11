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

## Updating CODEOWNERS

If you did not provide a Github team as Codeowners during onboarding, or your Github team changed, please update the [CODEOWNERS](.github/CODEOWNERS) file by adding your team slug in the format

```
/teams/<folder_name> @ingka-group-digital/<github_team_name>
```

This allows your team to approve future Pull Requests, removing the need of an approval by the Context team.

If doing this change in a Pull Request, you might see a warning similar to this:

```
CODEOWNERS errors
Unknown owner on line <>: make sure the team @ingka-group-digital/<github_team_name> exists, is publicly visible, and has write access to the repository
```

As long as the provided team exists in the Ingka organization, you can savely ignore this error. This appears because your Github team needs `write` permissions on the repository for the CODEOWNERS file to work, these permissions are automatically added by a workflow when merging your Pull Request to the `main` branch.
