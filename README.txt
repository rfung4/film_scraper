
Ensure that you have python (3.x) installed prior to setup

To install dependencies initially navigate to the project root folder in command prompt,
with the following command:

cd C:/example/path

Once within the root directory of the project folder execute the following commands to install
dependencies:

py -m pip install beautifulsoup4
py -m pip install lxml
py -m pip install requests
py -m pip install selenium
py -m pip install openpyxl

After installing dependencies to run a scape enter the following command:

py main.py 

Once all titles have been scraped and enriched execution will end and an excel file will be generated in the root directory.


To generate a summary spreadsheet navigate to the root directory and execute the following command:

py summary.py

This will generate a report using the latest schedule file, based on the year in the schedule spreadsheet name, in
the same directory.









