# cmcdermottJobProject
Senior Design and Development - Sprint 3

## Christian McDermott
#### Features
- This program takes from the GitHub Jobs API and stores them into a SQLite DB
- It then grabs from Stack Overflow's jobs and parses the feed into the SQLite DB
- This DB is then taken and displayed onto a map, where filters can be applied and details can be seen
#### Tests
##### Fourteen tests are built into the project
- Two tests check that data being taken in is not empty
- One test makes sure the DB exists
- One test checks that a specific company is in the DB
- One test checks that no primary keys are null within the DB
- Four tests run good and bad data from a pseudo-feed and a pseudo-API to make sure that bad data does not insert while good data does
- Four tests check that the HTML filters are properly filtering
- One test checks to make sure clicking on a dot on the map displays proper data
##### To run tests, use command 'python -m pytest'
