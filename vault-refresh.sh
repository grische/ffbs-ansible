#!/bin/bash
gpg2 --batch --use-agent --decrypt vault.gpg | \
  gpg2 --batch --use-agent \
  -r 59941A0EC8051123 \
  -r A2AEB64DC1042B74 \
  -r B294BC06C7552A7A \
  -r BFCDA6A312FDA911 \
  -r FAD89F12E404424E \
  -r C13000C733F89E91 \
  --encrypt > vault.gpg.new && mv vault.gpg.new vault.gpg
