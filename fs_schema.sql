-- File System SQL Commands for ECE 356 Project

-- Clean Up Existing Tables
DROP TABLE IF EXISTS GroupMemberships;
DROP TABLE IF EXISTS Directories;
DROP TABLE IF EXISTS ParentDirectory;
DROP TABLE IF EXISTS HardLinks;
DROP TABLE IF EXISTS SymbolicLinks;
DROP TABLE IF EXISTS RegularFileMetadata;
DROP TABLE IF EXISTS FileContents;
DROP TABLE IF EXISTS Files;
DROP TABLE IF EXISTS UserGroups;
DROP TABLE IF EXISTS Users;

-- Create Tables

CREATE TABLE Files (
    fileID INT,
    fileName VARCHAR(255),
    dateCreated DATE,
    permissionBits BINARY(9),
    groupOwnerID INT,
    authorID INT, 
    ownerID INT
);

CREATE TABLE Directories (
    fileID INT,
    dateModified DATE,
    dateLastOpened DATE,
);

CREATE TABLE ParentDirectory (
    fileID INT,
    parentDirectoryFileID INT
);

CREATE TABLE HardLinks (
    fileID INT,
    fileContentID INT
);

CREATE TABLE RegularFileMetadata (
    fileContentID INT,
    dateModified DATE,
    dateLastOpened DATE,
    size BIGINT
);

CREATE TABLE FileContents(
    fileContentID INT,
    lineNumber INT,
    lineContent BLOB
);

CREATE TABLE SymbolicLinks (
    fileID INT,
    dateModified DATE,
    dateLastOpened DATE,
    linkToFullPath TEXT
);

CREATE TABLE Users (
    userID INT,
    userName VARCHAR(32)
);

CREATE TABLE UserGroups (
    groupID INT,
    groupName VARCHAR(32)
);

CREATE TABLE GroupMemberships (
    groupID INT,
    userID INT
);


-- Primary Keys

ALTER TABLE Files ADD PRIMARY KEY (fileID);
ALTER TABLE Directories ADD PRIMARY KEY (fileID);
ALTER TABLE ParentDirectory ADD PRIMARY KEY (fileID);
ALTER TABLE HardLinks ADD PRIMARY KEY (fileID);
ALTER TABLE RegularFileMetadata ADD PRIMARY KEY (fileContentID);
ALTER TABLE FileContents ADD PRIMARY KEY (fileContentID, lineNumber);
ALTER TABLE Users ADD PRIMARY KEY (userID);
ALTER TABLE UserGroups ADD PRIMARY KEY (groupID);
ALTER TABLE GroupMemberships ADD PRIMARY KEY (groupID, userID);

-- Foreign Keys
ALTER TABLE Files ADD FOREIGN KEY (groupOwnerID) REFERENCES UserGroups(groupID);
ALTER TABLE Files ADD FOREIGN KEY (authorID) REFERENCES Users(userID);
ALTER TABLE Files ADD FOREIGN KEY (ownerID) REFERENCES Users(userID);
ALTER TABLE Directories ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE ParentDirectory ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE ParentDirectory ADD FOREIGN KEY (parentDirectoryFileID) REFERENCES Files(fileID);
ALTER TABLE RegularFiles ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE RegularFiles ADD FOREIGN KEY (fileContentID) REFERENCES FileContents(fileContentID);
ALTER TABLE SymbolicLinks ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE GroupMemberships ADD FOREIGN KEY (groupID) REFERENCES UserGroups(groupID);
ALTER TABLE GroupMemberships ADD FOREIGN KEY (userID) REFERENCES Users(userID);

-- Additional Indicies