# Preliminary Project Report

**Please tick appropriate project:**

- [ ] ENG4066P (BEng)
- [ ] ENG4110P (BEng)

---

**Student Name:** [Your Name]

**Student Matriculation Number:** [Your Student ID]

**Degree Programme:** [Your Degree Programme]

**Working Title of Project:** Interactive Distributed PBFT Consensus System with Real-time Visualization

**Name of Supervisor:** [Supervisor Name]

**Academic Year:** 2024-2025

---

## Introduction

Distributed consensus is a fundamental challenge in modern computing systems, particularly relevant to blockchain technology, distributed databases, and fault-tolerant systems. The Byzantine Generals Problem, first formalized by Lamport et al. (1982), represents a core challenge where system nodes must reach agreement despite the presence of faulty or malicious participants. The Practical Byzantine Fault Tolerance (PBFT) algorithm, proposed by Castro and Liskov (1999), provides an efficient solution capable of tolerating up to ⌊(n-1)/3⌋ Byzantine faults in a system of n nodes.

Despite its theoretical significance, PBFT and similar distributed consensus algorithms remain abstract concepts that are challenging to comprehend without practical experience. Traditional educational approaches rely on theoretical descriptions and static diagrams, which fail to capture the dynamic, interactive nature of distributed systems. This project addresses this pedagogical gap by developing an interactive, web-based platform where real users can embody network nodes and participate in the PBFT consensus process in real-time.

The system enables users to join via QR code or direct links, transforming abstract algorithmic concepts into tangible, experiential learning. By supporting Byzantine fault injection and providing real-time visualization of message flows, network topology, and consensus progress, the platform serves as both an educational tool and a research testbed for studying distributed consensus behavior under various conditions.

## Aims/Objectives of Project

### Primary Objectives

1. **Develop a Functional PBFT Implementation**
   - Implement the complete three-phase PBFT protocol (Pre-Prepare, Prepare, Commit)
   - Support configurable network topologies (fully-connected, ring, star, tree)
   - Enable dynamic user participation as network nodes (3-20 participants)
   - Ensure correct consensus achievement under Byzantine fault conditions

2. **Create Interactive User Experience**
   - Design dual-interface system: master control panel for instructors/researchers and simplified node interface for participants
   - Implement real-time WebSocket communication for sub-second message delivery
   - Develop QR code generation for seamless mobile device participation
   - Provide intuitive visualization of network topology and message propagation

3. **Enable Byzantine Fault Simulation**
   - Allow users to voluntarily act as Byzantine (malicious) nodes
   - Support multiple attack scenarios: malicious proposer, message tampering, silent nodes
   - Verify system fault tolerance maintains consensus with f < n/3 Byzantine nodes
   - Demonstrate consensus failure modes when fault threshold is exceeded

4. **Develop Educational and Research Value**
   - Create clear, real-time visualization of consensus phases and progress
   - Implement message history and statistics tracking
   - Support multiple consensus rounds for iterative learning
   - Provide exportable data for analysis and research purposes

### Secondary Objectives

- Optimize for mobile device responsiveness and accessibility
- Implement comprehensive testing suite for algorithm correctness
- Document system architecture and API for future extensions
- Create user guides for both technical and non-technical audiences

## Contingency Planning

### Technical Risks and Mitigation

**Risk 1: WebSocket Scalability Issues**
- *Potential Issue:* System performance degradation with 15-20 concurrent users
- *Mitigation:* Implement load testing early in development; optimize message routing algorithms; consider message batching if latency becomes problematic; fallback to reduced node limit (10-12) if necessary

**Risk 2: Cross-Platform Compatibility**
- *Potential Issue:* Inconsistent behavior across different browsers and mobile devices
- *Mitigation:* Prioritize Chrome and Safari testing (covering 80%+ users); use well-established libraries (Vue 3, Socket.IO) with proven cross-platform support; maintain list of supported browsers in documentation

**Risk 3: Byzantine Attack Complexity**
- *Potential Issue:* Difficulty in creating intuitive interface for complex attack scenarios
- *Mitigation:* Start with simplified attack options (become Byzantine: yes/no); expand to advanced options only if time permits; focus on demonstrating basic fault tolerance first

**Risk 4: Algorithm Correctness**
- *Potential Issue:* Subtle bugs in PBFT implementation leading to incorrect consensus
- *Mitigation:* Implement comprehensive unit tests for each protocol phase; create automated test scenarios with known outcomes; conduct code review with supervisor; reference established PBFT implementations

### Timeline and Scope Management

**Phased Development Approach:**

- **Phase 1 (Weeks 1-4):** Core PBFT algorithm and backend infrastructure
  - *Contingency:* If delayed, simplify to single topology (fully-connected) initially
  
- **Phase 2 (Weeks 5-8):** Basic frontend and real-time communication
  - *Contingency:* Use pre-built UI components if custom design is time-consuming
  
- **Phase 3 (Weeks 9-11):** Byzantine fault injection and visualization enhancements
  - *Contingency:* Limit to 2-3 attack scenarios if full range proves complex
  
- **Phase 4 (Weeks 12-14):** Testing, optimization, and documentation
  - *Contingency:* Protected time buffer for unexpected issues

**Scope Prioritization:**
- Must-have: Basic PBFT, 4+ nodes, visualization, at least one Byzantine attack type
- Should-have: Multiple topologies, mobile optimization, comprehensive statistics
- Nice-to-have: Historical replay, advanced attack scenarios, export functionality

### External Dependencies

**Risk 5: Third-party Library Issues**
- *Mitigation:* Select mature, well-maintained libraries; avoid cutting-edge versions; maintain local copies of dependencies

**Risk 6: Hardware/Network Failures**
- *Mitigation:* Regular code commits to version control (GitHub); maintain development on both local machine and cloud backup; document setup procedures for rapid environment reconstruction

## Resources Required

### Software and Development Tools

**Development Environment:**
- **Code Editor:** Visual Studio Code (already available)
- **Version Control:** Git and GitHub (free, already in use)
- **Node.js:** v18+ for frontend development (free, open source)
- **Python:** v3.9+ for backend development (free, open source)

**Frameworks and Libraries:**
- **Frontend:** Vue 3, Vue Router, Element Plus UI, Socket.IO Client, QRCode.js (all free, MIT/Apache licensed)
- **Backend:** FastAPI, Python-SocketIO, Uvicorn, Pydantic (all free, MIT licensed)

**Testing Tools:**
- Pytest for backend unit tests
- Vue Test Utils for frontend testing
- Browser DevTools for debugging
- Postman/Insomnia for API testing (free versions sufficient)

### Hardware and Infrastructure

**Development Machine:**
- Current laptop/desktop (sufficient for development)
- Minimum requirements: 8GB RAM, modern multi-core processor

**Testing Infrastructure:**
- **Local Testing:** Multiple browser instances on development machine
- **Multi-device Testing:** Personal mobile devices (phone/tablet) + university computer lab machines for cross-platform verification
- **Hosting (if required for demonstration):** Free tier services (Render, Railway, or Vercel) or university servers if available

### Knowledge Resources

**Technical Documentation:**
- Original PBFT paper (Castro & Liskov, 1999) - freely available
- Vue 3 official documentation - free online
- FastAPI documentation - free online
- WebSocket/Socket.IO specifications and tutorials - free online

**Academic Resources:**
- University library access for distributed systems textbooks
- IEEE Xplore and ACM Digital Library (via university subscription) for related research papers
- Supervisor consultations for algorithm verification and guidance

### Human Resources

**Essential:**
- **Project Supervisor:** Regular meetings for guidance, milestone reviews, and algorithm verification
- **Personal Time Commitment:** Estimated 15-20 hours per week for 14 weeks

**Optional but Beneficial:**
- Peer feedback from classmates for user interface testing
- Subject matter expert consultation (if available) for distributed systems validation
- Student volunteers for multi-user testing sessions (8-10 participants)

### Total Cost Estimate

**Direct Costs:** £0 (all software is open source; using existing hardware)

**Opportunity Costs:** Approximately 210-280 hours of development time over 14 weeks

This project is financially viable and requires no budget approval, relying entirely on freely available software tools and existing university resources.

---

**Document Prepared:** November 4, 2025

**Student Signature:** ________________________

**Date:** ________________________








