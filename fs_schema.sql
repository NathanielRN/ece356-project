-- File System SQL Commands for ECE 356 Project

-- Clean Up Existing Tables
DROP TABLE IF EXISTS GroupMemberships;
DROP TABLE IF EXISTS FileContents;
DROP TABLE IF EXISTS ParentDirectory;
DROP TABLE IF EXISTS SymbolicLinks;
DROP TABLE IF EXISTS HardLinks;
DROP TABLE IF EXISTS Directories;
DROP TABLE IF EXISTS RegularFileMetadata;
DROP TABLE IF EXISTS Files;
DROP TABLE IF EXISTS UserGroups;
DROP TABLE IF EXISTS Users;

-- Create Tables

CREATE TABLE Files (
    fileID INT NOT NULL AUTO_INCREMENT,
    fileName VARCHAR(255) NOT NULL,
    dateCreated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    permissionBits BINARY(2) NOT NULL DEFAULT X'01B6', -- 000 000 0 110 110 110
    groupOwnerID INT NOT NULL,
    authorID INT NOT NULL, 
    ownerID INT NOT NULL,
    PRIMARY KEY(fileID)
);

CREATE TABLE Directories (
    fileID INT NOT NULL,
    dateModified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dateLastOpened DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fileID)
);

CREATE TABLE ParentDirectory (
    fileID INT NOT NULL,
    parentDirectoryFileID INT NOT NULL,
    PRIMARY KEY (fileID)
);

CREATE TABLE HardLinks (
    fileID INT NOT NULL,
    fileContentID INT NOT NULL,
    PRIMARY KEY (fileID, fileContentID)
);

CREATE TABLE RegularFileMetadata (
    fileContentID INT NOT NULL AUTO_INCREMENT,
    dateModified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dateLastOpened DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    size BIGINT NOT NULL,
    PRIMARY KEY (fileContentID)
);

CREATE TABLE FileContents(
    fileContentID INT NOT NULL,
    lineNumber INT NOT NULL,
    lineContent LONGBLOB NOT NULL,
    PRIMARY KEY (fileContentID, lineNumber)
);

CREATE TABLE SymbolicLinks (
    fileID INT NOT NULL,
    dateModified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dateLastOpened DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    linkToFullPath TEXT NOT NULL,
    PRIMARY KEY (fileID)
);

CREATE TABLE Users (
    userID INT NOT NULL AUTO_INCREMENT,
    userName VARCHAR(32) NOT NULL,
    PRIMARY KEY (userID)
);

CREATE TABLE UserGroups (
    groupID INT NOT NULL AUTO_INCREMENT,
    groupName VARCHAR(32) NOT NULL,
    PRIMARY KEY (groupID)
);

CREATE TABLE GroupMemberships (
    groupID INT NOT NULL,
    userID INT NOT NULL,
    PRIMARY KEY (groupID, userID)
);

-- Foreign Keys
ALTER TABLE Files ADD FOREIGN KEY (groupOwnerID) REFERENCES UserGroups(groupID);
ALTER TABLE Files ADD FOREIGN KEY (authorID) REFERENCES Users(userID);
ALTER TABLE Files ADD FOREIGN KEY (ownerID) REFERENCES Users(userID);
ALTER TABLE Directories ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE ParentDirectory ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE ParentDirectory ADD FOREIGN KEY (parentDirectoryFileID) REFERENCES Directories(fileID);
ALTER TABLE HardLinks ADD FOREIGN KEY (fileContentID) REFERENCES RegularFileMetadata(fileContentID);
ALTER TABLE FileContents ADD FOREIGN KEY (fileContentID) REFERENCES RegularFileMetadata(fileContentID);
ALTER TABLE SymbolicLinks ADD FOREIGN KEY (fileID) REFERENCES Files(fileID);
ALTER TABLE GroupMemberships ADD FOREIGN KEY (groupID) REFERENCES UserGroups(groupID);
ALTER TABLE GroupMemberships ADD FOREIGN KEY (userID) REFERENCES Users(userID);

-- Additional Constraints
ALTER TABLE Users AUTO_INCREMENT=1000;
ALTER TABLE UserGroups AUTO_INCREMENT=1000;
ALTER TABLE Users ADD UNIQUE(userName);
ALTER TABLE UserGroups ADD UNIQUE(groupName);

-- Additional Indicies