## Non Profit

A Non profit app built on top of Frappe framework & ERPNext.


People who change the world need the tools to do it! The Non Profit Modules of ERPNext is designed for a non-profit organization, so that they can deliver well on their noble cause of a better world.


### Installation

Using bench, [install ERPNext](https://github.com/frappe/bench#installation) as mentioned here.

The `version-16` branch of this app is compatible with Frappe Framework v16 and ERPNext v16
(Python 3.14, Node 24). It also requires the [Payments](https://github.com/frappe/payments) app.

Once ERPNext is installed, add the payments and non_profit apps to your bench by running

```sh
$ bench get-app --branch version-16 payments
$ bench get-app --branch version-16 non_profit
```

After that, you can install non_profit app on required site by running

```sh
$ bench --site demo.com install-app non_profit
```


### Documentation

Read documentation at https://docs.erpnext.com/docs/v14/user/manual/en/non_profit/introduction


### License

GNU GPL V3
