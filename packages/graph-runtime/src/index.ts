import neo4j from "neo4j-driver";

const driver = neo4j.driver(
  process.env.NEO4J_URI || "bolt://localhost:7687",
  neo4j.auth.basic("neo4j", "password")
);

export async function registerEntity(
  label: string,
  properties: any
) {

  const session = driver.session();

  try {

    await session.run(
      `
      CREATE (n:${label} $props)
      `,
      {
        props: properties
      }
    );

  } finally {
    await session.close();
  }
}

export async function createRelation(
  fromId: string,
  toId: string,
  relation: string
) {

  const session = driver.session();

  try {

    await session.run(
      `
      MATCH (a {id:$fromId})
      MATCH (b {id:$toId})
      CREATE (a)-[:${relation}]->(b)
      `,
      {
        fromId,
        toId
      }
    );

  } finally {
    await session.close();
  }
}
