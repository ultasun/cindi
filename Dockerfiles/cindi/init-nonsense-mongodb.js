db = db.getSiblingDB("db0");
db.createUser({user: "root", pwd: "secret", roles: [ { role: "dbOwner", db: "db0"}]});

