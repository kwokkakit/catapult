"""Map of test units to improvement direction."""

from google.appengine.ext import ndb

from dashboard.models import anomaly


class UnitsToDirection(ndb.Model):
  """Data about improvement direction for one type of unit."""
  bigger_is_better = ndb.BooleanProperty(indexed=False)


def GetImprovementDirectionForUnit(units):
  """Returns the improvement direction for the given units string."""
  if not units:
    return anomaly.UNKNOWN
  entity = ndb.Key(UnitsToDirection, units).get()
  if not entity:
    return anomaly.UNKNOWN
  if entity.bigger_is_better:
    return anomaly.UP
  return anomaly.DOWN


def UpdateFromJson(units_dict):
  """Updates internal maps of units to direction from the given dictionary.

  Args:
    units_dict: A dictionary mapping unit names to dictionaries mapping
        the string 'improvement_direction' to either 'up' or 'down'.
  """
  unit_to_direction_entities = UnitsToDirection.query()

  existing_units = []
  # Update or remove existing UnitsToDirection entities.
  for units_to_direction_entity in unit_to_direction_entities:
    unit = units_to_direction_entity.key.id
    if unit not in units_dict:
      # Units not in the input dictionary will be removed from the datastore.
      units_to_direction_entity.key.delete()
      continue
    # TODO(qyearsley): Add test coverage. See http://crbug.com/447432
    existing_units.append(unit)

    # Update the improvement direction if necessary.
    improvement_direction = units_dict[unit]['improvement_direction']
    bigger_is_better = (improvement_direction == 'up')
    if units_to_direction_entity.bigger_is_better != bigger_is_better:
      units_to_direction_entity.bigger_is_better = bigger_is_better
      units_to_direction_entity.put()

  # Add new UnitsToDirection entities.
  for unit, value in units_dict.iteritems():
    if type(value) != dict:
      continue
    if unit not in existing_units:
      bigger_is_better = (value['improvement_direction'] == 'up')
      UnitsToDirection(id=unit, bigger_is_better=bigger_is_better).put()
