# cmcdermottJobProject
Senior Design and Development - Sprint 3

## Christian McDermott
#### Features
- This program takes from the GitHub Jobs API and stores them into a SQLite DB
- It then grabs from Stack Overflow's jobs and parses the feed into the SQLite DB
#### Tests
######Nine tests are built into the project
- Two tests check that data being taken in is not empty
- One test makes sure the DB exists
- One test checks that a specific company is in the DB
- One test checks that no primary keys are null within the DB
- Four tests run good and bad data from a pseudo-feed and a pseudo-API to make sure that bad data does not insert while good data does
#####To run tests, use command 'python -m pytest'
