# Automations

[← Back to README](../README.md)

Public Lands doesn't refresh on its own.  Press **Refresh USPL**, or use an automation.  Please keep automatic refreshes to no more than one every **10 minutes** while moving.

## Refresh when your location changes

Presses **Refresh USPL** when `zone.home` moves, at most once every 10 minutes.  If you set a different [location entity](configuration.md), use it as the trigger instead.

```yaml
alias: "USPL: Update via Button"
description: "Presses the Refresh USPL button when zone.home changes, throttled to once every 10 minutes."
triggers:
  - trigger: state
    entity_id: zone.home
conditions:
  - condition: template
    value_template: >
      {{ (as_timestamp(now()) - as_timestamp(this.attributes.last_triggered | default(0, true))) > 600 }}
actions:
  - action: button.press
    target:
      entity_id: button.refresh_uspl
mode: single
```

## Refresh when you park

If you have a binary sensor for whether the van is moving, press **Refresh USPL** when it changes from moving to stopped.  That captures where you actually parked, not the last update while driving, which is what you want when checking a campsite's jurisdiction.

## Check a place before you go

The `public_lands.lookup` action looks up any coordinate without changing the sensors.  See [Actions](sensors.md#actions).
