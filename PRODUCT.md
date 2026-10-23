# SolarOps Audit

<!-- impeccable:product-schema 1 -->

## Platform

web — FastAPI with packaged HTML, CSS and JavaScript, Python 3.12.

## Product Purpose

Read-only review of historical photovoltaic observations, estimated generation,
data quality, execution lineage and monthly reports. A separate loopback-only host
manager starts/stops already provisioned SolarOps containers. The portfolio demonstrates
data engineering and traceable failure/replay handling, not commercial traction.

## Users and operating context

The intended operator reviews a month, checks data quality and follows a plant
into its observations or generated report. This is a design assumption for the
portfolio, not a claim of validated customer research. Local demo on port 8502;
independent administrative origin 127.0.0.1:8504.

## Confirmed constraints

- User requires existing API, calculation logic and test contracts to remain.
- Estimated energy is never meter-measured energy, revenue or confirmed loss.
- Valid, invalid, missing and upstream interpolation remain distinct; upstream
  interpolation is an overlapping attribute, not a fourth quality category.
- No data is never converted to zero. Incomplete dates differ from missing slots.
- Public BR-PVGen and synthetic demo are labeled separately; sources stay traceable.
- Private repository; no customer data, public deployment or external messaging.
- Preserve raw data and original plans. Sensitive deletion requires permission.
- User authorized a completely new visual design, replacing the former UI.
- User chose grouped sidebar navigation and readable body/secondary text at 16/14px.
- Monthly report content belongs directly in the main document, without iframe
  or nested vertical scrolling; original report artifacts remain immutable.
- Admin controls existing local SolarOps resources only. No delete, prune, SQL,
  arbitrary commands, remote Docker context, or control of unrelated projects.

## Scope and evidence

Seven grouped destinations: overview, plants, quality, reports, runs, sources,
and system administration. Shared styled selectors and monthly report vocabulary.
See [data contract](docs/data-contract.md), [sources](docs/data-sources.md),
[planning](plan.md) and [handoff](handoff.md). Real customers, business performance,
physical-device usability and screen-reader behavior remain unverified.

## ONS collection status extension

The existing Sources destination also reads ONS collection attempts and the last
successful monthly cursor from the connected store. Compose and kind stores remain
independent. This UI does not observe scheduler liveness or trigger collection.
Source-native MWmed and unspecified timezone stay separate from estimated energy.
