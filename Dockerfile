# Dockerfile.dry-run
#
# Builds an isolated test environment for m1well-toolsuite.sh - ephemeral,
# disposable, zero risk to the real machine.
#
# IMPORTANT: deliberately NO sudo package installed. If a sudo call is
# still lurking anywhere in the old or new script, it crashes immediately
# with "sudo: command not found" - that's the actual test.
#
# Build:  docker build -t toolsuite-dryrun -f Dockerfile.dry-run .
# Run:    docker run --rm -it toolsuite-dryrun
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      vim \
      zsh \
      openssh-client \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# plain regular user, no root, no admin/sudo group - 1:1 your current
# state on the MacBook
RUN useradd -m -s /bin/bash devuser
USER devuser
WORKDIR /home/devuser

# replicates exactly the setup step from your script header:
# mkdir m1well-toolsuite && cd m1well-toolsuite && git clone ... && cd env-setup
RUN mkdir -p m1well-toolsuite \
    && cd m1well-toolsuite \
    && git clone https://github.com/m1well/env-setup.git

# copy updated toolsuite script to test it
COPY --chown=devuser:devuser m1well-toolsuite.sh /home/devuser/m1well-toolsuite/env-setup/m1well-toolsuite.sh
RUN chmod +x /home/devuser/m1well-toolsuite/env-setup/m1well-toolsuite.sh

WORKDIR /home/devuser/m1well-toolsuite/env-setup
CMD ["/bin/bash"]

