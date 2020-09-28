# Export Import Contenstack Using Python
*Work in progress*

## Prerequisites:
* Contentstack Account.
* Install Python 3 (Developed using Python 3.7.6 on Macbook).
* Install Python packages:
  * `pip install requests`
  * `pip install nested-lookup`
  * `pip install inquirer`

## How to use:
* Run `python app.py` and answer questions that you get asked.
* If in trouble: Contact Oskar.
* Exported things go to a folder called `content`.

## Current Limitations:
* Does not export assets when this is written.
* Does only import stack structure at this point.
* If you don't have a delivery token defined for environment, it is only possible to export all entries (not using the delivery token).
* Circular dependencies (references) in content model breaks content model import.
* Something else: Contact Oskar.

## ToDo:
* Add Assets Export
* Add Asset/Entries Import
* Add Optional Publishing and Workflow Stage Setting on Import
* Allow exporting Environments without having the delivery token defined
