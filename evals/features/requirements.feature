# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md, plugin/templates/STATE.md
Feature: requirements stage

  Background:
    Given initialized repos
    And the requirements stage has run in each for a small CLI feature request

  Scenario: Output is well-formed
    Then at least 90% of runs leave a valid task folder, STATE.md and REQUIREMENTS.md

  Scenario: Output quality
    Then the judge scores average at least 4 with none below 3
