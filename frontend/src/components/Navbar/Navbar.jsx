import React from "react";
import { SocialIcon } from "react-social-icons";
import "./navbar.css";

function Navbar() {
  return (
    <header>
      <div className="socialicons-container">
        <SocialIcon
          url="https://github.com/baniasbaabe/SocialMediaGPT"
          fgColor="#454545"
          bgColor="transparent"
          target="_blank"
        ></SocialIcon>
        <SocialIcon
          url="https://www.linkedin.com/in/banias/"
          fgColor="#454545"
          bgColor="transparent"
          target="_blank"
        ></SocialIcon>
      </div>
    </header>
  );
}

export default Navbar;
