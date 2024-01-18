This project is no longer actively maintained. For current needs, please consider using the Contentstack CLI. While the code here may still be of interest, it is not being updated.

# Contentstack Cloner using Python
Export and/or Import Stack structure and/or all or a subset of entries and assets.
*Work in progress*

**Not officially supported by Contentstack**

Please use the issue tracker here for any questions, ideas, issues or comments.

## Prerequisites:
* Contentstack Account.
* Install Python 3 (Developed using Python 3.7.6 on Macbook).
* Install Python packages:
  * `pip install requests`
  * `pip install inquirer`
  * `pip install python-benedict`

## How to use:
* Run `python app.py` and answer questions that you get asked.
* If in trouble: [Open an issue](https://github.com/Contentstack-Solutions/contentstack-python-cloner/issues/new/choose)
* Exported content goes to a folder called `data/stacks` (variables in config module).

## Notes:
* By default enabled webhooks are disabled on import, minimizing the risk of triggering to production environments.
    * See the `disableWebhooks` variable in the config module if you want to change that.

## Current Limitations:
* Content Revision's are not exported/imported. Only newest versions, or what is currently published is exported.
* Because only a single version of entries and assets is exported it is not possible to publish separate versions when imported (Like is possible between environments).
* Roles do not map to specific entries or assets on import, since role import happens before entries or assets are imported.
* System Roles (Admin, Content Manager, Developer) are not modified on import.
* Older versioned stacks are not imported correctly at the moment.
    * Token names are unique in newer stacks, not older ones.
    * Workflow export issue.
    * References of older version are not imported correctly and return an error.
* Known bugs:
    * Environment Export with Delivery Token does not work as of now.
    * Webhooks with identical names issue. Only exports a single webhook in that case.


## ToDo:
* Add Automatic Unit Testing and Mocking.
* Add Optional Publishing and Workflow Stage Setting on Import.
* Refactor.
* Make an application, e.g. https://realpython.com/python-application-layouts/
* Make it possible to import Demo stacks from Github (Lower Priority).
* Any ideas: [Submit an issue](https://github.com/Contentstack-Solutions/contentstack-python-cloner/issues/new/choose). Pull Requests also welcomed.
