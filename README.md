# Export Import Contenstack Using Python
*Work in progress*

## Prerequisites:
* Contentstack Account.
* Install Python 3 (Developed using Python 3.7.6 on Macbook).
* Install Python packages:
  * `pip install requests`
  * `pip install nested-lookup`
  * `pip install inquirer`
  * `pip install python-benedict`

## How to use:
* Run `python app.py` and answer questions that you get asked.
* If in trouble: Contact Oskar.
* Exported content goes to a folder called `data/stacks` (variables in config module).

## Current Limitations:
* Circular dependencies (references) in content model breaks content model import. (Will be fixed)
* Entry Import still a bit buggy. Refactoring needed along with reference mapping. Asset mapping should work.
* Content Revision's are not exported/imported. Only newest versions, or what is currently published is exported.
* Because only a single version of entries and assets is exported it is not possible to publish separate versions when imported (Like is possible between environments).
* Something else? Contact Oskar.

## ToDo:
* Add Automatic Unit Testing and Mocking.
* Fix circular dependencies.
* Add Optional Publishing and Workflow Stage Setting on Import.
* Refactor.
* Make an application, e.g. https://realpython.com/python-application-layouts/
* Make it possible to import Demo stacks from Github (Lower Priority).
* Any ideas: Contact Ron or Oskar.
