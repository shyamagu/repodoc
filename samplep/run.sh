#!/bin/bash

# Compile the Java files
javac -d out -sourcepath src src/jp/test/front/Main.java

# Run the compiled Java program
java -cp out jp.test.front.Main