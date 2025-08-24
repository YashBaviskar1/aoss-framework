import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};

function Hero() {
  return (
    <section className="relative flex flex-col items-center justify-center text-center px-6 py-24 z-10">
      <div className="flex items-center space-x-4 mb-6">
        <img
          src="https://www.secuinfra.com/wp-content/uploads/SOAR_Kreise-1.png"
          alt="AOSS Logo"
          className="w-16 h-16"
        />
        <motion.h1
          className="text-5xl font-bold"
          initial="hidden"
          whileInView="visible"
          variants={fadeUp}
          transition={{ duration: 0.8 }}
        >
          Automated Orchestration Framework (AOSS)
        </motion.h1>
      </div>
      <motion.p
        className="text-lg text-gray-600 max-w-2xl"
        initial="hidden"
        whileInView="visible"
        variants={fadeUp}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        A modern framework for SRE and System Administration to automate,
        scale, and simplify infrastructure management.
      </motion.p>
    </section>
  );
}

export default Hero;
