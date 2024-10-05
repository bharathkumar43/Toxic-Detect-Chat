create database databse;
use databse;
create table users(
	username varchar(250),
    password varchar(250));
create table messages(
	username varchar(250),
    message varchar(250),
    timestamp datetime);