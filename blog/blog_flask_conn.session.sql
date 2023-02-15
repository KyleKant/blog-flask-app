DROP TABLE IF EXISTS reply;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS users;
CREATE TABLE users(
    id INT PRIMARY KEY AUTO_INCREMENT,
    username varchar(70) UNIQUE NOT NULL,
    email varchar(255) UNIQUE NOT NULL,
    password varchar(255) NOT NULL,
    registered_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed boolean NOT NULL DEFAULT false,
    confirmed_at timestamp NULL

);
CREATE TABLE post(
    id INT PRIMARY KEY AUTO_INCREMENT,
    author_id INT NOT NULL,
    created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title varchar(255) NOT NULL,
    body text not null,
    votes int NOT NULL,
    FOREIGN KEY (author_id) REFERENCES users (id)
);
CREATE TABLE reply(
    id INT PRIMARY KEY auto_increment,
    created_by varchar(255) NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    post_id int NOT NULL,
    reply text NOT NULL,
    votes_up int NOT NULL DEFAULT 0,
    votes_down int NOT NULL DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users (username),
    FOREIGN KEY (post_id) REFERENCES post (id)
);
