# SLO Resource

On our journey to provide more and more useful features to our users in Context, we have started to build an **SLO as a Service** feature into the platform.

⚠️ Currently, this feature is still in active development and things can be changed before a full release. We still want to provide this feature to as many of our users as possible, to get an early feedback and decide if we are moving in the correct direction. ⚠️

This documentation is about the possible values to set in an SLO resource. You can find more detailed information [in Allen](https://allen.ingka.com/docs/default/component/context/slos-as-a-service/).

## Values

| Value                      | Description                                                                                                                                                                                                                          | Example                                                                                                                                   | Mandatory |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| metadata.name              | Name of the SLO. Has to be prefixed with the teamname and unique.                                                                                                                                                                    | `kontext-exampleslo`                                                                                                                      | Yes       |
| spec.description           | Short description of the SLO                                                                                                                                                                                                         | `This is an example.`                                                                                                                     | No        |
| spec.location              | Location to apply this SLO. Either `gcp-eu` or `alicloud-cn`                                                                                                                                                                         | `gcp-eu`                                                                                                                                  | Yes       |
| spec.target                | Target of the SLO. Has to be a string of a number.                                                                                                                                                                                   | `"99.0"`                                                                                                                                  | Yes       |
| spec.window                | Window in which to monitor the SLO                                                                                                                                                                                                   | `30d`                                                                                                                                     | Yes       |
| spec.labels                | Any labels to add to the SLO metric. The [oi-o11y-framework](https://github.com/ingka-group-digital/oi-o11y-framework/blob/main/docs/ADR/ADR-OPI-02.md) labels are mandatory.                                                        | See [example](#example-definition)                                                                                                        | Yes       |
| spec.indicator             | Indicator which records the SLO. Supported are `bool_gauge`, `latency`, `latencyNative` and `ratio`                                                                                                                                  | See [example](#example-definition). Check the [Pyrra repository](https://github.com/pyrra-dev/pyrra/tree/main/examples) for more examples | Yes       |
| spec.indicator.\_.grouping | Grouping on a specific label. Be advised, as soon as grouping is used, the generic SLO dashboards will **NOT** work anymore. See [docs](https://allen.ingka.com/docs/default/component/context/slos-as-a-service/#pyrra-dashboards). |                                                                                                                                           | No        |

## Example definition

```yaml
---
apiVersion: "context.ingka.com/v1"
kind: SLO
metadata:
  name: kontext-exampleslo
spec:
  description: "This is a test SLO for Kontext"
  location: "gcp-eu"
  target: "99.0"
  window: "30d"
  labels:
    - name: "service.name"
      value: "k8s_operator"
    - name: "deployment.environment.name"
      value: "dev"
    - name: "ingka.legal_company"
      value: "ingka"
    - name: "ingka.system_name"
      value: "CONTEXT"
    - name: "ingka.team"
      value: "DPS-OI-NextGen"
    - name: "ingka.version"
      value: "0.5.0"
  indicator:
    ratio:
      grouping:
        - "deployment_environment_name"
      errors:
        metric: o11ydemo_test_counter{success="false"}
      total:
        metric: o11ydemo_test_counter
```
