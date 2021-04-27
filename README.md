## Dynamic Inventory from Auvik's API for many Automation Tools

- Create inventory on the fly with our Inventory Classes.
- Use the command line tool to generate folder/file structure.
- Use CSV/Excel documents to update inventory pulled from Auvik.
  > This is done to overcome Auvik's API providing a list of all IPs assigned to host instead of a single IP. There is no way to get the IP currently being used by Auvik's probes at this time.

### Get Started
1. Install the package using your favorite Python package manager.
  ```
  pip install auvik_inventory
  ```

2. Provide your credentials in the _config.yaml_ file or just type *auvik-inv* to configure interactively.
  > See example "config_example.yaml" with comments.

3. Use the inventory with Ansible, Nornir, Netmiko, AutoIE, etc.


### Get Started Development
1. Clone the repo.
  ```
  git clone https://github.com/IE-OnDemand/auvik_inventory
  ```
  OR
  ```
  git clone git@github.com:IE-OnDemand/auvik_inventory
  ```

2. Create a new branch for your work.  Please follow our branch naming schema.
  Branching Schema:
    - Use dash to separate words within a section and underscores to separate each section.
    - First part of branch name is a high-level name for what you are fixing or creating along with any related ticket number(s).
    - Second part of branch name is your IE username.
    - Last part of branch name is the date formated as: 04-01-2021 (2 digit month, 2 digit day, 4 digit year, all seperated by dashes).
  ```
  git branch -b fix-spelling_rlaney_04-25-2021
  ```

3. Now make your changes to the new branch and commit.
  ```
  git commit -m "Fixed spelling"
  ```

4. When done run the tests. If there are failures, you must correct them.  All tests must pass before approvals are provided. 
  ```
  make tests
  ```

5. Create a pull-request.  Once approved, your new branch will be incorporated into the production branch.
