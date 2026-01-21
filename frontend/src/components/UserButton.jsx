import { UserButton } from "@clerk/clerk-react";

const CustomUserButton = () => {
  return (
    <UserButton
      appearance={{
        elements: {
          userButtonBox: "flex items-center",
          userButtonTrigger: "focus:shadow-none",
          userButtonOuterIdentifier: "text-base-content",
          avatarBox: "w-8 h-8",
        }
      }}
    />
  );
};

export default CustomUserButton;