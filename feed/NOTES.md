# Notes

## Testing
### Fixtures
- Fixtures must not get out of sync with the database model. Be careful! Also, when you dump the data for the fixture run the command  `python manage.py dumpdata -e contenttypes -e admin -e auth.Permission --natural-foreign --indent=2` instead of the plain `python manage.py dumpdata` to avoid "contenttype" and other database errors.