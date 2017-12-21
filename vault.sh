#!/bin/bash
gpg2 --batch --use-agent --decrypt vault.gpg | grep -v '#'
