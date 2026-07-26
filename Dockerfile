# Dockerfile
#
# Builds an isolated test environment for m1well-toolsuite.sh - ephemeral,
# disposable, zero risk to the real machine.
#
# IMPORTANT: deliberately NO sudo package installed. If a sudo call is
# still lurking anywhere in the old or new script, it crashes immediately
# with "sudo: command not found" - that's the actual test.
#
# Build:  docker build -t toolsuite-dryrun .
# Run:    docker run --rm -it toolsuite-dryrun
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      vim \
      curl \
      zsh \
      openssh-client \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# plain regular user, no root, no admin/sudo group - 1:1 your current
# state on the MacBook
RUN useradd -m -s /bin/bash devuser
USER devuser
WORKDIR /home/devuser

# copy the LOCAL working tree into place - this tests exactly what is on disk
# (including local cli/* changes), not the pushed GitHub version. TOOLSUITE_HOME
# resolves to /home/devuser/m1well-toolsuite (parent of the script dir).
RUN mkdir -p /home/devuser/m1well-toolsuite/env-setup
COPY --chown=devuser:devuser . /home/devuser/m1well-toolsuite/env-setup
RUN chmod +x /home/devuser/m1well-toolsuite/env-setup/m1well-toolsuite.sh

WORKDIR /home/devuser/m1well-toolsuite/env-setup
CMD ["/bin/bash"]
