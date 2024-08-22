# Team Resource

After onboarding through [Allen](https://allen.ingka.com/get-access/context-onboarding), a new resource YAML will be created for your team. This file holds all information about your team and can be adjusted to update your configuration in Context.

Some values are currently read only. To change these values, please reach out to the Context team through our [Slack Channel](https://ingka.slack.com/archives/C051G9AL88K). The values viable to change might be updated over time.

## Values

| Value                     | Description                                                                                                       | Changeable | Additional                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| metadata.name             | Name of your team in the backend - this is a unique value                                                         | No         |                                                                                    |
| spec.displayName          | Name of your team in Grafana                                                                                      | Yes        |                                                                                    |
| spec.owner                | Responsible for the team                                                                                          | Yes        |                                                                                    |
| spec.locations            | List of locations the team is onboarded. Valid options are `gcp-eu` and `alicloud-cn`                             | Yes        | If changed, tokens will still stay the same and just be valid in all locations     |
| spec.roles                | Azure AD group names for your team - Add / remove AD groups to add/remove access                                  | Yes        |                                                                                    |
| spec.tenants.name         | A tenant name in Context                                                                                          | No         |                                                                                    |
| spec.tenants.cost_center  | Cost Center for this tenant                                                                                       | Yes        |                                                                                    |
| spec.tenants.project_code | Project Code for this tenant                                                                                      | Yes        |                                                                                    |
| spec.tenants.read_access  | Resource names of teams with `read` access to this tenant - value needs to be the `metadata.name` of the new team | Yes        | Will add a Loki datasource to this teams Grafana organization to allow log sharing |
| spec.tenants.write_access | Which teams are allowed to create write tokens - currently not supported yet                                      | Yes        |                                                                                    |
| spec.tokens               | Information of tokens owned by your team, currently _read only_                                                   | No         |                                                                                    |
