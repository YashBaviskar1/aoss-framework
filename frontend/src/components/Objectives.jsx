import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};

function Objectives() {
  const objectives = [
    {
      title: "Automated Orchestration",
      description:
        "Simplify complex SRE and system administration tasks by automating orchestration workflows.",
    },
    {
      title: "Enhanced Reliability",
      description:
        "Improve uptime and minimize risks with real-time monitoring, alerting, and automated recovery.",
    },
    {
      title: "Seamless Scalability",
      description:
        "Ensure your infrastructure grows effortlessly with intelligent scaling and load balancing.",
    },
    {
      title: "Efficient Management",
      description:
        "Reduce manual effort with centralized dashboards and automated system insights.",
    },
  ];

  return (
    <section className="px-6 py-16 bg-white bg-opacity-90 z-10 relative">
      <h2 className="text-3xl font-semibold text-center mb-12">
        Key Objectives
      </h2>
      <div className="flex flex-col gap-8 max-w-3xl mx-auto">
        {objectives.map((obj, index) => (
          <motion.div
            key={index}
            className="bg-white shadow-md rounded-2xl p-6 border border-gray-200 hover:shadow-xl transition"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            whileHover={{ scale: 1.05, rotate: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, delay: index * 0.2 }}
          >
            <h3 className="text-xl font-semibold mb-3">{obj.title}</h3>
            <p className="text-gray-600">{obj.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export default Objectives;
